import clsx from 'clsx';

export default function StatusBadge({ status }: { status: string }) {
  const getBadgeStyle = (s: string) => {
    switch (s) {
      case 'SUBMITTED':
      case 'CONFIRMED':
        return 'bg-green-100 text-green-800';
      case 'OTP_REQUIRED':
      case 'CAPTCHA_REQUIRED':
      case 'REVIEW_REQUIRED':
      case 'UNKNOWN_QUESTION':
      case 'LOGIN_REQUIRED':
        return 'bg-yellow-100 text-yellow-800';
      case 'ERROR':
      case 'BLOCKED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <span className={clsx('px-2.5 py-0.5 rounded-full text-xs font-medium', getBadgeStyle(status))}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}
