type PanelProps = {
  title?: string;
  hint?: string;
  children: React.ReactNode;
  className?: string;
};

export function Panel({ title, hint, children, className = "" }: PanelProps) {
  return (
    <section className={`panel ${className}`.trim()}>
      {title ? <h2>{title}</h2> : null}
      {hint ? <p className="hint">{hint}</p> : null}
      {children}
    </section>
  );
}
