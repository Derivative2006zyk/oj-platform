export function showToast(message: string, type: 'info' | 'success' | 'error' = 'info') {
  const div = document.createElement('div')
  div.className = `oj-toast oj-toast-${type}`
  div.textContent = message
  
  Object.assign(div.style, {
    position: 'fixed',
    top: '20px',
    left: '50%',
    transform: 'translateX(-50%) translateY(-20px)',
    padding: '10px 20px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '500',
    zIndex: '99999',
    opacity: '0',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    color: '#fff',
    backgroundColor: type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6',
    pointerEvents: 'none'
  })

  document.body.appendChild(div)

  requestAnimationFrame(() => {
    div.style.opacity = '1'
    div.style.transform = 'translateX(-50%) translateY(0)'
  })

  setTimeout(() => {
    div.style.opacity = '0'
    div.style.transform = 'translateX(-50%) translateY(-20px)'
    setTimeout(() => {
      if (document.body.contains(div)) {
        document.body.removeChild(div)
      }
    }, 300)
  }, 3000)
}