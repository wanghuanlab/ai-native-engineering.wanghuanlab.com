import axios, { type AxiosError, type AxiosRequestConfig } from 'axios'

/** 后端统一错误响应（RFC 9457），见 contracts/openapi/common.yaml */
export interface ProblemDetail {
  status: number
  title: string
  code: string
  detail?: string
  traceId?: string
  errors?: { field: string; message: string }[]
}

export class ApiError extends Error {
  readonly problem: ProblemDetail

  constructor(problem: ProblemDetail) {
    super(problem.detail ?? problem.title)
    this.name = 'ApiError'
    this.problem = problem
  }
}

export const http = axios.create({ timeout: 30_000 })

type ApiErrorHandler = (error: ApiError) => void
let errorHandler: ApiErrorHandler | undefined

/** 由应用注册统一的错误提示（例如弹出消息并展示追踪号） */
export function setApiErrorHandler(handler: ApiErrorHandler): void {
  errorHandler = handler
}

function isProblemDetail(value: unknown): value is ProblemDetail {
  return typeof value === 'object' && value !== null && 'code' in value && 'status' in value
}

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const data = error.response?.data
    const apiError = new ApiError(
      isProblemDetail(data)
        ? data
        : { status: error.response?.status ?? 0, title: '网络异常，请稍后重试', code: 'C0001' },
    )
    errorHandler?.(apiError)
    return Promise.reject(apiError)
  },
)

/** 生成的接口函数通过它发起请求，直接返回响应体 */
export const request = <T>(config: AxiosRequestConfig): Promise<T> =>
  http.request<T>(config).then((response) => response.data)
