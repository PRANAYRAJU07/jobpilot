export default function StatCard({ title, value, icon: Icon, colorClass }: any) {
  return (
    <div className="bg-white rounded-lg shadow p-6 flex items-center">
      <div className={`p-3 rounded-full mr-4 ${colorClass}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div>
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
      </div>
    </div>
  );
}
