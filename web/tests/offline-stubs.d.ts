declare var process: { env: Record<string, string | undefined>; cwd(): string }
interface RequestInit { next?: { revalidate?: number } }
declare namespace React {
  type ReactNode = any
  type CSSProperties = Record<string, string | number | undefined>
  type ChangeEvent<T = any> = { target: T }
  type KeyboardEvent<T = any> = { key: string; target: T }
}
declare namespace JSX {
  interface IntrinsicAttributes { key?: any }
  interface ElementChildrenAttribute { children: {} }
  interface IntrinsicElements { [elemName: string]: any }
}
declare module 'react' {
  export type FormEvent<T = any> = any
  export type ChangeEvent<T = any> = React.ChangeEvent<T>
  export type KeyboardEvent<T = any> = React.KeyboardEvent<T>
  export function useState<T>(initial: T): [T, (next: T | ((old: T) => T)) => void]
  export function useEffect(fn: () => void | (() => void), deps: any[]): void
  export function useMemo<T>(fn: () => T, deps: any[]): T
  export function useRef<T>(initial: T): { current: T }
  export function useRef<T>(initial: T | null): { current: T | null }
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: any[]): T
}
declare module 'next' {
  export type Metadata = any
  export type NextConfig = any
  export namespace MetadataRoute { type Sitemap = any[]; type Robots = any }
}
declare module 'next/link' { const Link: any; export default Link }
declare module 'next/image' { const Image: any; export default Image }
declare module 'next/navigation' { export function useRouter(): { push(path: string): void }; export function usePathname(): string; export function notFound(): never }
declare module '*.module.css' { const classes: Record<string,string>; export default classes }
declare module '*.css' {}
