export type FormMessageValue = {
  text: string;
  type?: "success" | "error" | "default";
};

export function FormMessage({ message }: { message?: FormMessageValue }) {
  if (!message?.text) return <div className="message" />;

  return <div className={`message ${message.type || ""}`.trim()}>{message.text}</div>;
}
