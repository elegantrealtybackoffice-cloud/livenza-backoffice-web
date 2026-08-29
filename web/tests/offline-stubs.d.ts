declare var process: { env: Record<string, string | undefined>; cwd(): string }
interface RequestInit { next?: { revalidate?: number } }
declare namespace React { type ReactNode = any }
declare namespace JSX {
  interface IntrinsicAttributes { key?: any }
  interface IntrinsicElements { [elemName: string]: any }
}
declare module 'react' {
  export type FormEvent<T = any> = any
  export type ChangeEvent<T = any> = { target: T }
  export function useState<T>(initial: T): [T, (next: T | ((old: T) => T)) => void]
  export function useEffect(fn: () => void | (() => void), deps: any[]): void
  export function useMemo<T>(fn: () => T, deps: any[]): T
}
declare module 'next' {
  export type Metadata = any
  export type NextConfig = any
  export namespace MetadataRoute { type Sitemap = any[]; type Robots = any }
}
declare module 'next/link' { const Link: any; export default Link }
declare module 'next/navigation' { export function useRouter(): { push(path: string): void }; export function notFound(): never }
declare module '*.module.css' { const classes: Record<string,string>; export default classes }
declare module '*.css' {}
