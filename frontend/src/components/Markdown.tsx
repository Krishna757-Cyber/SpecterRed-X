// Minimal, SAFE Markdown renderer. It does NOT use dangerouslySetInnerHTML and
// never parses raw HTML — it tokenizes a safe subset (headings, tables, lists,
// bold/italic/code/links, blockquotes) into React elements. This is sufficient
// for our server-generated reports and avoids an injection surface.
import { Fragment, type ReactNode } from 'react'

function renderInline(text: string, keyBase: string): ReactNode[] {
  const nodes: ReactNode[] = []
  // Order matters: code first so ** inside code is untouched.
  const regex = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\[[^\]]+\]\([^)]+\))|(_[^_]+_)/g
  let last = 0
  let m: RegExpExecArray | null
  let i = 0
  while ((m = regex.exec(text))) {
    if (m.index > last) nodes.push(text.slice(last, m.index))
    const tok = m[0]
    if (tok.startsWith('`')) {
      nodes.push(<code key={`${keyBase}-c${i}`} className="mono rounded bg-surface px-1 py-0.5 text-[0.85em] text-cyan">{tok.slice(1, -1)}</code>)
    } else if (tok.startsWith('**')) {
      nodes.push(<strong key={`${keyBase}-b${i}`} className="font-semibold text-ink">{tok.slice(2, -2)}</strong>)
    } else if (tok.startsWith('[')) {
      const mm = /\[([^\]]+)\]\(([^)]+)\)/.exec(tok)!
      const href = mm[2]
      const safe = /^https?:\/\//i.test(href) ? href : '#'
      nodes.push(
        <a key={`${keyBase}-l${i}`} href={safe} target="_blank" rel="noreferrer" className="text-cyan hover:underline">
          {mm[1]}
        </a>,
      )
    } else if (tok.startsWith('_')) {
      nodes.push(<em key={`${keyBase}-i${i}`} className="italic">{tok.slice(1, -1)}</em>)
    }
    last = m.index + tok.length
    i++
  }
  if (last < text.length) nodes.push(text.slice(last))
  return nodes
}

export function Markdown({ source }: { source: string }) {
  const lines = source.split('\n')
  const blocks: ReactNode[] = []
  let i = 0
  let key = 0

  while (i < lines.length) {
    const line = lines[i]

    // Table: header | --- | rows
    if (line.includes('|') && i + 1 < lines.length && /^\s*\|?[\s:-]+\|/.test(lines[i + 1])) {
      const header = splitRow(line)
      const rows: string[][] = []
      i += 2
      while (i < lines.length && lines[i].includes('|')) {
        rows.push(splitRow(lines[i]))
        i++
      }
      blocks.push(
        <div key={key++} className="my-3 overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="text-left text-muted">
              <tr>{header.map((h, j) => <th key={j} className="border-b border-[var(--border-subtle)] px-2 py-1.5">{renderInline(h, `h${key}-${j}`)}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((r, ri) => (
                <tr key={ri} className="border-b border-[var(--border-subtle)]">
                  {r.map((c, ci) => <td key={ci} className="px-2 py-1.5 text-ink">{renderInline(c, `r${key}-${ri}-${ci}`)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      )
      continue
    }

    if (/^#{1,6}\s/.test(line)) {
      const level = line.match(/^#+/)![0].length
      const content = line.replace(/^#+\s/, '')
      const cls = level === 1 ? 'text-xl font-bold mt-5 mb-2 text-ink' : level === 2 ? 'text-base font-semibold mt-5 mb-2 text-ink border-l-2 border-cyan pl-2' : 'text-sm font-semibold mt-3 mb-1 text-ink'
      blocks.push(<p key={key++} className={cls}>{renderInline(content, `hd${key}`)}</p>)
      i++
      continue
    }

    if (/^>\s/.test(line)) {
      blocks.push(
        <blockquote key={key++} className="my-2 border-l-2 border-warning/50 bg-warning/5 px-3 py-2 text-xs text-muted">
          {renderInline(line.replace(/^>\s/, ''), `bq${key}`)}
        </blockquote>,
      )
      i++
      continue
    }

    if (/^[-*]\s/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^[-*]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s/, ''))
        i++
      }
      blocks.push(
        <ul key={key++} className="my-2 space-y-1 pl-4 text-sm text-muted">
          {items.map((it, j) => <li key={j} className="list-disc">{renderInline(it, `li${key}-${j}`)}</li>)}
        </ul>,
      )
      continue
    }

    if (line.trim() === '') {
      i++
      continue
    }

    blocks.push(<p key={key++} className="my-1.5 text-sm leading-relaxed text-muted">{renderInline(line, `p${key}`)}</p>)
    i++
  }

  return <Fragment>{blocks}</Fragment>
}

function splitRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((c) => c.trim())
}
