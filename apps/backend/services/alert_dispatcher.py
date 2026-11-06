import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
import httpx
import redis
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models

logger = logging.getLogger("jobpilot.alert_dispatcher")


class AlertDispatcherService:
    """
    Dispatches verified, cross-validated job & internship alerts containing the direct
    original application link to the candidate via:
      1. Email (SMTP / Gmail App Password OR connected Gmail OAuth API)
      2. WhatsApp (Twilio WhatsApp API, Meta WhatsApp Cloud API, or CallMeBot/Webhook)
      3. In-App Notification + Live WebSocket Broadcast
    """
    def __init__(self, db: Session):
        self.db = db

    def dispatch_job_match_alert(
        self,
        job: models.Job,
        profile: models.CandidateProfile,
        match_data: Dict[str, Any],
        force: bool = False,
    ) -> Dict[str, Any]:
        user = profile.user or self.db.query(models.User).filter_by(id=profile.user_id).first()
        if not user:
            return {"sent": False, "reason": "User not found"}

        pref = self.db.query(models.NotificationPreference).filter_by(user_id=user.id).first()
        dedupe_key = f"job_match_alert:{user.id}:{job.id}"

        if not force:
            existing = self.db.query(models.Notification).filter_by(
                user_id=user.id,
                dedupe_key=dedupe_key
            ).first()
            if existing:
                return {"sent": False, "reason": "Already alerted for this job", "notification_id": str(existing.id)}

        apply_link = job.apply_url or job.url or ""
        score = match_data.get("relevance_score", 0)
        matched_skills = match_data.get("matched_skills", [])
        missing_skills = match_data.get("missing_skills", [])
        domain = match_data.get("domain_category") or job.domain_category or "Tech"
        role_type = "Internship" if job.is_internship else (job.role_level or "Full-Time")

        title = f"🎯 {score}% Match: {job.title} at {job.company} ({role_type})"
        body = (
            f"Verified {domain} {role_type} on {job.source} ({job.location or 'Remote/India'}). "
            f"Matched skills: {', '.join(matched_skills[:8]) or 'Profile Match'}. "
            f"Apply directly: {apply_link}"
        )

        # Target recipient addresses
        target_email = (
            (pref.alert_email if pref and pref.alert_email else None)
            or profile.alert_email
            or user.email
        )
        target_whatsapp = (
            (pref.whatsapp_number if pref and pref.whatsapp_number else None)
            or profile.whatsapp_number
            or profile.phone
        )

        email_enabled = (
            (pref.email_enabled if pref and pref.email_enabled is not None else True)
            and (profile.email_alerts_enabled if profile.email_alerts_enabled is not None else True)
        )
        whatsapp_enabled = (
            (pref.whatsapp_enabled if pref and pref.whatsapp_enabled is not None else True)
            and (profile.whatsapp_alerts_enabled if profile.whatsapp_alerts_enabled is not None else True)
        )

        channels_result = {
            "in_app": True,
            "email": {"attempted": False, "status": "SKIPPED", "recipient": target_email},
            "whatsapp": {"attempted": False, "status": "SKIPPED", "recipient": target_whatsapp},
        }

        if email_enabled and target_email:
            channels_result["email"]["attempted"] = True
            email_res = self.send_email_alert(
                recipient_email=target_email,
                job=job,
                profile=profile,
                match_data=match_data,
                apply_link=apply_link,
            )
            channels_result["email"].update(email_res)

        if whatsapp_enabled and target_whatsapp:
            channels_result["whatsapp"]["attempted"] = True
            wa_res = self.send_whatsapp_alert(
                phone_number=target_whatsapp,
                job=job,
                match_data=match_data,
                apply_link=apply_link,
            )
            channels_result["whatsapp"].update(wa_res)

        # Save Notification record in DB
        payload = {
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "source": job.source,
            "apply_url": apply_link,
            "relevance_score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "domain_category": domain,
            "is_fresh": job.is_fresh,
            "is_genuine": job.is_genuine,
            "channels": channels_result,
        }

        notif = self.db.query(models.Notification).filter_by(
            user_id=user.id,
            dedupe_key=dedupe_key
        ).first()

        if not notif:
            notif = models.Notification(
                user_id=user.id,
                candidate_id=profile.id,
                job_id=job.id,
                type="JOB_MATCH",
                priority="HIGH" if score >= 80 else "NORMAL",
                title=title,
                body=body,
                payload=payload,
                dedupe_key=dedupe_key,
                status="DELIVERED",
                sent_at=datetime.utcnow(),
                delivered_at=datetime.utcnow(),
            )
            self.db.add(notif)
            try:
                self.db.commit()
                self.db.refresh(notif)
            except IntegrityError:
                self.db.rollback()
        else:
            notif.payload = payload
            notif.sent_at = datetime.utcnow()
            self.db.commit()

        # Broadcast live WebSocket event via Redis Pub/Sub
        self._publish_ws_event(str(user.id), notif, payload)

        return {
            "sent": True,
            "notification_id": str(notif.id) if notif else None,
            "apply_url": apply_link,
            "channels": channels_result,
        }

    def send_email_alert(
        self,
        recipient_email: str,
        job: models.Job,
        profile: models.CandidateProfile,
        match_data: Dict[str, Any],
        apply_link: str,
    ) -> Dict[str, Any]:
        """
        Sends a rich HTML + Plain-Text job alert email with the direct application link
        via SMTP (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD) or logs ready-to-send payload
        if SMTP credentials are not yet configured in .env.
        """
        score = match_data.get("relevance_score", 0)
        matched_reqs = match_data.get("matched_requirements", [])
        missing_skills = match_data.get("missing_skills", [])
        role_badge = "Internship" if job.is_internship else (job.role_level or "Full-Time")
        domain = match_data.get("domain_category") or job.domain_category or "Engineering"

        subject = f"[JobPilot AI] {score}% Skill Match: {job.title} at {job.company} ({role_badge})"

        matched_rows_html = "".join(
            f"<li><strong>{r.get('skill')}</strong> — <em>{', '.join(r.get('evidence', []))}</em></li>"
            for r in matched_reqs
        ) or "<li>Matches your core domain profile</li>"

        missing_html = (
            f"<p style='color:#b91c1c;font-size:13px;'><strong>Skills to brush up:</strong> {', '.join(missing_skills)}</p>"
            if missing_skills else "<p style='color:#15803d;font-size:13px;'><strong>100% of required skills verified on your resume!</strong></p>"
        )

        html_body = f"""
        <div style="font-family:Inter,Arial,sans-serif;max-width:620px;margin:0 auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
          <div style="background:linear-gradient(135deg,#2563eb,#4f46e5);color:#ffffff;padding:20px 24px;">
            <span style="background:rgba(255,255,255,0.2);padding:4px 10px;border-radius:999px;font-size:12px;font-weight:600;">
              ✓ Verified Genuine · {job.source} · {role_badge}
            </span>
            <h2 style="margin:12px 0 4px 0;font-size:20px;">{job.title}</h2>
            <p style="margin:0;font-size:14px;opacity:0.9;">{job.company} · {job.location or 'India / Remote'}</p>
          </div>
          <div style="padding:24px;background:#ffffff;">
            <div style="display:flex;gap:16px;margin-bottom:16px;background:#f8fafc;padding:14px;border-radius:8px;border:1px solid #e2e8f0;">
              <div>
                <div style="font-size:12px;color:#64748b;text-transform:uppercase;">Cross-Validation Score</div>
                <div style="font-size:24px;font-weight:700;color:#16a34a;">{score}% Match</div>
              </div>
              <div style="margin-left:24px;">
                <div style="font-size:12px;color:#64748b;text-transform:uppercase;">Domain Fit</div>
                <div style="font-size:15px;font-weight:600;color:#1e293b;margin-top:4px;">{domain}</div>
              </div>
            </div>
            <h3 style="font-size:14px;color:#1e293b;margin-bottom:8px;">Verified Skills Matched from Your Resume:</h3>
            <ul style="font-size:13px;color:#334155;line-height:1.6;padding-left:20px;">
              {matched_rows_html}
            </ul>
            {missing_html}
            <div style="margin-top:24px;text-align:center;">
              <a href="{apply_link}" style="display:inline-block;background:#2563eb;color:#ffffff;font-weight:600;font-size:15px;padding:12px 28px;border-radius:8px;text-decoration:none;">
                Apply Directly on {job.source} →
              </a>
            </div>
            <p style="margin-top:16px;font-size:12px;color:#64748b;word-break:break-all;">
              Direct Application Link: <a href="{apply_link}" style="color:#2563eb;">{apply_link}</a>
            </p>
          </div>
        </div>
        """

        text_body = (
            f"JobPilot AI — Verified Job Match ({score}%)\n\n"
            f"Role: {job.title}\n"
            f"Company: {job.company}\n"
            f"Location: {job.location or 'India / Remote'}\n"
            f"Platform: {job.source} ({role_badge})\n"
            f"Domain: {domain}\n"
            f"Matched Skills: {', '.join(match_data.get('matched_skills', []))}\n"
            f"Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}\n\n"
            f"Apply Directly Here: {apply_link}\n"
        )

        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM") or smtp_user or "alerts@jobpilot.ai"

        if not smtp_user or not smtp_password:
            logger.info(f"[Email Alert Prepared -> {recipient_email}] Subject: {subject} | Link: {apply_link}")
            return {
                "status": "QUEUED_IN_APP_SMTP_UNCONFIGURED",
                "subject": subject,
                "apply_url": apply_link,
                "note": "Set SMTP_USER and SMTP_PASSWORD (e.g. Gmail App Password) in .env to enable live SMTP delivery.",
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = recipient_email
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from, [recipient_email], msg.as_string())

            logger.info(f"Email alert successfully sent to {recipient_email} for job {job.id}")
            return {"status": "SENT", "subject": subject, "apply_url": apply_link}
        except Exception as e:
            logger.error(f"SMTP Email alert failed for {recipient_email}: {e}")
            return {"status": "FAILED", "error": str(e), "apply_url": apply_link}

    def send_whatsapp_alert(
        self,
        phone_number: str,
        job: models.Job,
        match_data: Dict[str, Any],
        apply_link: str,
    ) -> Dict[str, Any]:
        """
        Sends an instant WhatsApp job match message containing the direct application link.
        Supports:
          1. Twilio WhatsApp API (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM)
          2. Meta WhatsApp Cloud API (WHATSAPP_CLOUD_TOKEN, WHATSAPP_PHONE_NUMBER_ID)
          3. CallMeBot Free Personal WhatsApp API (CALLMEBOT_API_KEY) or Custom Webhook (WHATSAPP_WEBHOOK_URL)
        """
        score = match_data.get("relevance_score", 0)
        matched_skills = ", ".join(match_data.get("matched_skills", [])[:6]) or "Profile Match"
        role_badge = "Internship" if job.is_internship else (job.role_level or "Full-Time")

        wa_message = (
            f"🎯 *JobPilot AI — {score}% Skill Match*\n"
            f"*{job.title}* at *{job.company}*\n"
            f"📍 {job.location or 'India / Remote'} | 🏷️ {role_badge} ({job.source})\n"
            f"✅ *Matched Skills:* {matched_skills}\n"
            f"🔗 *Apply Directly:* {apply_link}"
        )

        clean_phone = "".join(c for c in phone_number if c.isdigit() or c == "+")
        if clean_phone and not clean_phone.startswith("+"):
            clean_phone = "+" + clean_phone

        # 1. Twilio WhatsApp API
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

        if twilio_sid and twilio_token:
            try:
                to_wa = clean_phone if clean_phone.startswith("whatsapp:") else f"whatsapp:{clean_phone}"
                from_wa = twilio_from if twilio_from.startswith("whatsapp:") else f"whatsapp:{twilio_from}"
                resp = httpx.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json",
                    data={"From": from_wa, "To": to_wa, "Body": wa_message},
                    auth=(twilio_sid, twilio_token),
                    timeout=15.0,
                )
                if resp.status_code in (200, 201):
                    return {"status": "SENT", "provider": "TWILIO", "apply_url": apply_link}
                return {"status": "FAILED", "provider": "TWILIO", "error": resp.text[:200]}
            except Exception as e:
                return {"status": "FAILED", "provider": "TWILIO", "error": str(e)}

        # 2. Meta WhatsApp Cloud API
        meta_token = os.getenv("WHATSAPP_CLOUD_TOKEN")
        meta_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        if meta_token and meta_phone_id:
            try:
                resp = httpx.post(
                    f"https://graph.facebook.com/v19.0/{meta_phone_id}/messages",
                    headers={"Authorization": f"Bearer {meta_token}", "Content-Type": "application/json"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": clean_phone.lstrip("+"),
                        "type": "text",
                        "text": {"preview_url": True, "body": wa_message},
                    },
                    timeout=15.0,
                )
                if resp.status_code in (200, 201):
                    return {"status": "SENT", "provider": "META_CLOUD", "apply_url": apply_link}
                return {"status": "FAILED", "provider": "META_CLOUD", "error": resp.text[:200]}
            except Exception as e:
                return {"status": "FAILED", "provider": "META_CLOUD", "error": str(e)}

        # 3. CallMeBot WhatsApp API or Custom Webhook
        callmebot_key = os.getenv("CALLMEBOT_API_KEY")
        if callmebot_key:
            try:
                url = (
                    f"https://api.callmebot.com/whatsapp.php"
                    f"?phone={quote_plus(clean_phone)}&text={quote_plus(wa_message)}&apikey={quote_plus(callmebot_key)}"
                )
                resp = httpx.get(url, timeout=15.0)
                if resp.status_code == 200:
                    return {"status": "SENT", "provider": "CALLMEBOT", "apply_url": apply_link}
            except Exception as e:
                return {"status": "FAILED", "provider": "CALLMEBOT", "error": str(e)}

        webhook_url = os.getenv("WHATSAPP_WEBHOOK_URL")
        if webhook_url:
            try:
                resp = httpx.post(
                    webhook_url,
                    json={"phone": clean_phone, "message": wa_message, "apply_url": apply_link},
                    timeout=10.0,
                )
                if resp.status_code in (200, 201, 202):
                    return {"status": "SENT", "provider": "WEBHOOK", "apply_url": apply_link}
            except Exception as e:
                return {"status": "FAILED", "provider": "WEBHOOK", "error": str(e)}

        # Fallback: provide instant click-to-chat wa.me deep link and log message
        wa_deeplink = f"https://wa.me/{clean_phone.lstrip('+')}?text={quote_plus(wa_message)}"
        logger.info(f"[WhatsApp Alert Prepared -> {clean_phone}] {wa_message}")
        return {
            "status": "READY_DEEP_LINK",
            "provider": "WA_ME_LINK",
            "whatsapp_url": wa_deeplink,
            "message_preview": wa_message,
            "note": "Configure TWILIO_ACCOUNT_SID, WHATSAPP_CLOUD_TOKEN, or CALLMEBOT_API_KEY in .env for automated background push.",
        }

    def _publish_ws_event(self, user_id: str, notif: Optional[models.Notification], payload: Dict[str, Any]):
        if not notif:
            return
        try:
            r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, socket_timeout=1)
            ws_payload = {
                "event": "NOTIFICATION_CREATED",
                "data": {
                    "id": str(notif.id),
                    "type": notif.type,
                    "priority": notif.priority,
                    "title": notif.title,
                    "body": notif.body,
                    "payload": payload,
                    "created_at": notif.created_at.isoformat() if notif.created_at else datetime.utcnow().isoformat(),
                },
            }
            r.publish(f"user_events:{user_id}", json.dumps(ws_payload))
            r.publish("global_events", json.dumps(ws_payload))
        except Exception:
            pass
