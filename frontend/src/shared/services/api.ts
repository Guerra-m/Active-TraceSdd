import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

// ─── Token store en memoria (D-01) ───────────────────────────────────────────
let _accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  _accessToken = token
}

export function getAccessToken(): string | null {
  return _accessToken
}

// ─── Cola de reintentos (D-02) ────────────────────────────────────────────────
type QueueItem = {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

let _isRefreshing = false
let _queue: QueueItem[] = []

function processQueue(error: unknown, token: string | null): void {
  _queue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token!)
    }
  })
  _queue = []
}

// ─── Función de logout forzado (D-03) ─────────────────────────────────────────
let _forceLogoutFn: (() => void) | null = null

export function registerForceLogout(fn: () => void): void {
  _forceLogoutFn = fn
}

function forceLogout(): void {
  setAccessToken(null)
  if (_forceLogoutFn) {
    _forceLogoutFn()
  } else {
    window.location.href = '/login'
  }
}

// ─── Instancia Axios ───────────────────────────────────────────────────────────
export const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // envía la cookie httpOnly del refresh token
})

// Interceptor de request: inyectar Bearer token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Interceptor de response: cola de reintentos en 401
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    if (_isRefreshing) {
      // Encolar el request mientras el refresh está en vuelo
      return new Promise<string>((resolve, reject) => {
        _queue.push({ resolve, reject })
      })
        .then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
        .catch((err) => Promise.reject(err))
    }

    originalRequest._retry = true
    _isRefreshing = true

    try {
      const { data } = await axios.post<{ access_token: string }>(
        '/api/auth/refresh',
        {},
        { withCredentials: true },
      )
      const newToken = data.access_token
      setAccessToken(newToken)
      processQueue(null, newToken)
      originalRequest.headers.Authorization = `Bearer ${newToken}`
      return api(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError, null)
      forceLogout()
      return Promise.reject(refreshError)
    } finally {
      _isRefreshing = false
    }
  },
)
