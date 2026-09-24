import { createContext, useCallback, useContext, useEffect, useState } from 'react'

const ModalContext = createContext(null)

const defaults = {
  info: { title: 'Information', icon: 'i' },
  success: { title: 'Success', icon: '✓' },
  warning: { title: 'Please check', icon: '!' },
  error: { title: 'Something went wrong', icon: '!' },
}

function normalizeModal(input, title, message) {
  if (typeof input === 'string') {
    const type = defaults[input] ? input : 'info'
    return { type, title: title || defaults[type].title, message: message || '' }
  }

  const type = defaults[input?.type] ? input.type : 'info'
  return {
    type,
    title: input?.title || defaults[type].title,
    message: input?.message || '',
    duration: input?.duration,
  }
}

function MessageModal({ modal, onClose }) {
  useEffect(() => {
    if (!modal) return undefined

    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [modal, onClose])

  if (!modal) return null
  const preset = defaults[modal.type] || defaults.info

  return (
    <div className="message-modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose()
    }}>
      <section
        className={`message-modal message-modal-${modal.type}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="message-modal-title"
      >
        <div className="message-modal-icon" aria-hidden="true">{preset.icon}</div>
        <div className="message-modal-copy">
          <h2 id="message-modal-title">{modal.title}</h2>
          <p>{modal.message}</p>
        </div>
        <button className="message-modal-close" type="button" onClick={onClose} aria-label="Close message">×</button>
        <button className="button message-modal-action" type="button" onClick={onClose}>Continue</button>
      </section>
    </div>
  )
}

function MessageModalBridge({ showModal }) {
  useEffect(() => {
    if (typeof document === 'undefined') return undefined

    function inspect(element) {
      if (!(element instanceof HTMLElement)) return
      const isError = element.classList.contains('form-error')
      const isSuccess = element.classList.contains('success-message')
      if (!isError && !isSuccess) return

      const message = element.textContent.replace(/\s+/g, ' ').trim()
      if (!message || element.dataset.modalMessage === message) return
      element.dataset.modalMessage = message
      showModal({
        type: isError ? 'error' : 'success',
        title: isError ? 'Action could not be completed' : 'Saved successfully',
        message,
      })
    }

    function inspectTree(node) {
      if (node.nodeType !== Node.ELEMENT_NODE) return
      inspect(node)
      node.querySelectorAll?.('.success-message, .form-error').forEach(inspect)
    }

    document.querySelectorAll('.success-message, .form-error').forEach(inspect)
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'characterData') inspect(mutation.target.parentElement)
        mutation.addedNodes.forEach(inspectTree)
      })
    })
    observer.observe(document.body, { childList: true, characterData: true, subtree: true })
    return () => observer.disconnect()
  }, [showModal])

  return null
}

export function ModalProvider({ children }) {
  const [modal, setModal] = useState(null)

  const closeModal = useCallback(() => setModal(null), [])
  const showModal = useCallback((input, title, message) => {
    setModal(normalizeModal(input, title, message))
  }, [])

  useEffect(() => {
    document.body.classList.add('modal-messages-enabled')
    return () => document.body.classList.remove('modal-messages-enabled')
  }, [])

  useEffect(() => {
    if (!modal || modal.duration === 0) return undefined
    const duration = modal.duration || (modal.type === 'error' ? 6000 : 4200)
    const timer = window.setTimeout(closeModal, duration)
    return () => window.clearTimeout(timer)
  }, [modal, closeModal])

  return (
    <ModalContext.Provider value={{ showModal, closeModal }}>
      {children}
      <MessageModalBridge showModal={showModal} />
      <MessageModal modal={modal} onClose={closeModal} />
    </ModalContext.Provider>
  )
}

export function useModal() {
  const context = useContext(ModalContext)
  if (!context) throw new Error('useModal must be used inside ModalProvider')
  return context
}
