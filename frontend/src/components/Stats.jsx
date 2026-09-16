import { Skeleton } from "./ui";

export function StatGrid({ children }) {
  return <section className="stats">{children}</section>;
}

export function Stat({ label, value, hint, tone = "", loading }) {
  return (
    <div className="stat">
      <span>{label}</span>
      {loading ? (
        <strong className="stat-skeleton">
          <Skeleton width="60%" height={22} />
        </strong>
      ) : (
        <strong className={tone}>{value}</strong>
      )}
      {hint && <small>{hint}</small>}
    </div>
  );
}
