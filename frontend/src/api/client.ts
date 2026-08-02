import axios from 'axios'
import { apiConfig } from '@/api/config'

export const API_BASE_URL = apiConfig.baseURL ?? 'http://localhost:8000'

export const client = axios.create(apiConfig)
