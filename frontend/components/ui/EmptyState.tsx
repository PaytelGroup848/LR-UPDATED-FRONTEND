export function EmptyState({ message = "No records found." }: { message?: string }) {
  return <div className="empty">{message}</div>;
}
