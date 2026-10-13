import api from '../utils/axios'

export interface UploadedImage {
  id: number
  url: string
}

export async function uploadUserImage(file: File): Promise<UploadedImage> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.post<UploadedImage>('/images/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}