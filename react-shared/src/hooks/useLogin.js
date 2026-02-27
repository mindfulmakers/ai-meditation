import { useState, useCallback } from 'react'
import { login } from '../lib/allauth'

export default function useLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [response, setResponse] = useState({ fetching: false, content: null })

  const handleSubmit = useCallback(() => {
    setResponse(prev => ({ ...prev, fetching: true }))
    
    login({ email, password })
      .then((content) => {
        setResponse(prev => ({ ...prev, content }))
      })
      .catch((error) => {
        console.error(error)
        window.alert(error)
      })
      .finally(() => {
        setResponse(prev => ({ ...prev, fetching: false }))
      })
  }, [email, password])

  const resetForm = useCallback(() => {
    setEmail('')
    setPassword('')
    setResponse({ fetching: false, content: null })
  }, [])

  return {
    email,
    setEmail,
    password,
    setPassword,
    response,
    handleSubmit,
    resetForm,
    isLoading: response.fetching,
    errors: response.content?.errors
  }
}