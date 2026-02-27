import FormErrors from '../components/FormErrors'
import { Link } from 'react-router-dom'
import { useConfig } from '../auth'
import ProviderList from '../socialaccount/ProviderList'
import Button from '../components/Button'
import WebAuthnLoginButton from '../mfa/WebAuthnLoginButton'
import useLogin from '../hooks/useLogin'

export default function Login () {
  const { email, setEmail, password, setPassword, handleSubmit, isLoading, errors } = useLogin()
  const config = useConfig()
  const hasProviders = config.data.socialaccount?.providers?.length > 0
  return (
    <div>
      <h1>Login</h1>
      <p>
        No account? <Link to='/account/signup'>Sign up here.</Link>
      </p>

      <FormErrors errors={errors} />

      <div><label>Email <input value={email} onChange={(e) => setEmail(e.target.value)} type='email' required /></label>
        <FormErrors param='email' errors={errors} />
      </div>
      <div><label>Password: <input value={password} onChange={(e) => setPassword(e.target.value)} type='password' required /></label>
        <Link to='/account/password/reset'>Forgot your password?</Link>
        <FormErrors param='password' errors={errors} />
      </div>
      <Button disabled={isLoading} onClick={handleSubmit}>Login</Button>
      {config.data.account.login_by_code_enabled
        ? <Link className='btn btn-secondary' to='/account/login/code'>Send me a sign-in code</Link>
        : null}
      <WebAuthnLoginButton>Sign in with a passkey</WebAuthnLoginButton>
      {hasProviders
        ? <>
          <h2>Or use a third-party</h2>
          <ProviderList callbackURL='/account/provider/callback' />
        </>
        : null}
    </div>
  )
}
