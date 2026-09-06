declare namespace JSX { interface IntrinsicElements { [elemName: string]: any } }
declare namespace React { interface ChangeEvent<T = any> { target: T } interface KeyboardEvent<T = any> { key: string; target: T } }
declare module 'react' {
  export type SetStateAction<T> = T | ((prev: T) => T);
  export type Dispatch<T> = (value: T) => void;
  export function useState<T>(initial: T | (() => T)): [T, Dispatch<SetStateAction<T>>];
  export function useEffect(effect: () => void | (() => void), deps?: readonly unknown[]): void;
  export function useMemo<T>(factory: () => T, deps: readonly unknown[]): T;
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: readonly unknown[]): T;
  export function useRef<T>(initial: T): { current: T };
  export function useRef<T>(initial: T | null): { current: T | null };
}
declare module 'next' { export type Metadata = { title?: string; description?: string; manifest?: string }; }
declare module 'next/image' { const Image: any; export default Image; }
declare module '*.module.css' { const classes: Record<string, string>; export default classes; }
declare var process: { env: Record<string, string | undefined> };
interface RequestInit { next?: { revalidate?: number }; }
