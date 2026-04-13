export function subHours(hours: number): Date {
  return new Date(Date.now() - hours * 60 * 60 * 1000);
}
