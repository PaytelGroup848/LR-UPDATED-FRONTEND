type Stat = {
  label: string;
  value: number | string;
  tone?: "blue" | "green" | "amber" | "red";
};

const toneMap = {
  blue: "blueText",
  green: "greenText",
  amber: "amberText",
  red: "redText"
};

export function StatsGrid({ stats }: { stats: Stat[] }) {
  return (
    <section className="grid">
      {stats.map((stat) => (
        <div className="card" key={stat.label}>
          <div className="label">{stat.label}</div>
          <div className={`value ${toneMap[stat.tone || "blue"]}`}>{stat.value}</div>
        </div>
      ))}
    </section>
  );
}
