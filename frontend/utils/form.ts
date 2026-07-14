export function formPayload<T extends Record<string, unknown>>(form: HTMLFormElement): T {
  const data = new FormData(form);
  const payload: Record<string, unknown> = {};

  data.forEach((value, key) => {
    payload[key] = value;
  });

  return payload as T;
}
