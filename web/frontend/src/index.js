import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cathy_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const register    = (data) => api.post('/auth/register', data)
export const login       = (data) => api.post('/auth/login', data)
export const getChats    = ()     => api.get('/chat/chats')
export const createChat  = (title) => api.post('/chat/chats', { title })
export const deleteChat  = (id)   => api.delete(`/chat/chats/${id}`)
export const getMessages = (chatId) => api.get(`/chat/chats/${chatId}/messages`)

export default api
