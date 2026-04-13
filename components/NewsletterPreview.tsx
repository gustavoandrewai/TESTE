export function NewsletterPreview({ html }: { html: string }) {
  return <article className="card" dangerouslySetInnerHTML={{ __html: html }} />;
}
