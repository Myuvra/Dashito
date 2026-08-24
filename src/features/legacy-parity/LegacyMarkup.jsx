import { createElement, useMemo } from 'react'
import LegacyDisclosure from './LegacyDisclosure'

const sensitiveTabs = new Set(['tab-poverty', 'tab-social', 'tab-gini'])

const attributeMap = {
  class: 'className',
  for: 'htmlFor',
  colspan: 'colSpan',
  rowspan: 'rowSpan',
  tabindex: 'tabIndex',
  readonly: 'readOnly',
  maxlength: 'maxLength',
  minlength: 'minLength',
  cellpadding: 'cellPadding',
  cellspacing: 'cellSpacing',
  frameborder: 'frameBorder',
  crossorigin: 'crossOrigin',
  autofocus: 'autoFocus',
  contenteditable: 'contentEditable',
  spellcheck: 'spellCheck',
  srcset: 'srcSet',
}

const eventMap = {
  onclick: 'onClick',
  onchange: 'onChange',
  oninput: 'onInput',
  onblur: 'onBlur',
  onfocus: 'onFocus',
  onsubmit: 'onSubmit',
}

const booleanAttributes = new Set(['disabled', 'required', 'multiple', 'open', 'hidden', 'controls', 'autoplay', 'loop', 'muted'])

// El HTML no permite nodos de texto en blanco como hijos directos de estos
// contenedores; React (createElement) los rechaza con un warning de hidratación.
// El Legacy los deja por indentación, así que los descartamos al reconstruir.
const whitespaceIntolerantParents = new Set(['table', 'thead', 'tbody', 'tfoot', 'tr', 'colgroup'])

function camelCase(property) {
  if (property.startsWith('--')) return property
  return property.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())
}

function styleObject(styleText) {
  return Object.fromEntries(styleText.split(';').map((declaration) => {
    const separator = declaration.indexOf(':')
    if (separator < 0) return null
    const property = declaration.slice(0, separator).trim()
    const value = declaration.slice(separator + 1).trim()
    return property && value ? [camelCase(property), value] : null
  }).filter(Boolean))
}

function localAsset(value) {
  if (!value || /^(?:[a-z]+:|#|\/)/i.test(value)) return value
  return `/data/${value.replace(/^\.\//, '')}`
}

function legacyHandler(source) {
  return function handleLegacyEvent(event) {
    const result = Function('event', source).call(event.currentTarget, event)
    if (result === false) event.preventDefault()
  }
}

function reactAttribute(element, attribute) {
  const rawName = attribute.name
  const lowerName = rawName.toLowerCase()
  const value = attribute.value
  if (eventMap[lowerName]) return [eventMap[lowerName], legacyHandler(value)]
  if (lowerName === 'style') return ['style', styleObject(value)]
  if (lowerName === 'checked') return ['defaultChecked', true]
  if (lowerName === 'selected') return ['defaultValue', value || true]
  if (lowerName === 'value' && /^(?:input|select|textarea)$/i.test(element.tagName)) return ['defaultValue', value]
  if (booleanAttributes.has(lowerName)) return [attributeMap[lowerName] || lowerName, true]
  if (lowerName === 'href' || lowerName === 'src') return [lowerName, localAsset(value)]
  if (lowerName.startsWith('data-') || lowerName.startsWith('aria-')) return [lowerName, value]
  const name = attributeMap[lowerName] || (rawName.includes('-') ? camelCase(rawName) : rawName)
  return [name, value]
}

function toReact(node, key, context = { sensitive: false }) {
  if (node.nodeType === Node.TEXT_NODE) return node.textContent
  if (node.nodeType !== Node.ELEMENT_NODE || /^(?:script|noscript)$/i.test(node.tagName)) return null
  const id = node.getAttribute('id')
  const nextContext = id && sensitiveTabs.has(id) ? { ...context, sensitive: true } : context
  if (nextContext.sensitive && node.tagName.toLowerCase() === 'span' && node.textContent.trim() === '♡') return null
  const props = { key }
  for (const attribute of node.attributes) {
    const [name, value] = reactAttribute(node, attribute)
    props[name] = value
  }
  const storyAnchor = node.tagName.toLowerCase() === 'a' ? node.getAttribute('href') : null
  if (storyAnchor?.startsWith('#story-')) {
    props.onClick = (event) => {
      event.preventDefault()
      document.getElementById(storyAnchor.slice(1))?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
  const dropWhitespace = whitespaceIntolerantParents.has(node.tagName.toLowerCase())
  const children = [...node.childNodes]
    .filter((child) => !(dropWhitespace && child.nodeType === Node.TEXT_NODE && !child.textContent.trim()))
    .map((child, index) => toReact(child, `${key}-${index}`, nextContext))
    .filter((child) => child !== null)
  const classNames = node.getAttribute('class')?.split(/\s+/) || []
  if (classNames.includes('sources-box') || classNames.includes('formulas-box')) {
    return createElement(LegacyDisclosure, { ...props, as: node.tagName.toLowerCase() }, ...children)
  }
  return createElement(node.tagName.toLowerCase(), props, ...children)
}

export default function LegacyMarkup({ html }) {
  const nodes = useMemo(() => {
    if (!html) return []
    const documentFragment = new DOMParser().parseFromString(html, 'text/html')
    return [...documentFragment.body.childNodes].map((node, index) => toReact(node, `legacy-${index}`)).filter(Boolean)
  }, [html])
  return nodes
}
