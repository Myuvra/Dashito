import { Children, cloneElement, createElement, isValidElement, useId, useState } from 'react'

export default function LegacyDisclosure({ as = 'section', children, ...props }) {
  const [open, setOpen] = useState(false)
  const contentId = useId()
  const items = Children.toArray(children)
  const headingIndex = items.findIndex((child) => isValidElement(child) && /^h[1-6]$/i.test(String(child.type)))
  const heading = headingIndex >= 0 ? items[headingIndex] : null
  const content = items.filter((_, index) => index !== headingIndex)
  const label = heading?.props?.children || 'Información complementaria'

  const disclosureHeading = heading
    ? cloneElement(heading, { className: `${heading.props.className || ''} legacy-disclosure__heading`.trim() },
      <button
        type="button"
        className="legacy-disclosure__trigger"
        aria-expanded={open}
        aria-controls={contentId}
        onClick={() => setOpen((value) => !value)}
      >
        <span>{label}</span>
        <span className="legacy-disclosure__chevron" aria-hidden="true">⌄</span>
      </button>)
    : null

  return createElement(as, { ...props, 'data-disclosure': open ? 'open' : 'closed' },
    disclosureHeading,
    <div id={contentId} className="legacy-disclosure__content" hidden={!open}>{content}</div>,
  )
}
