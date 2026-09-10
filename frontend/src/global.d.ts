declare module "react" {
  export function useEffect(fn: () => void | (() => void), deps: unknown[]): void;
  export function useState<T>(initial: T): [T, (value: T) => void];
}
declare module "react-dom/client" {
  export function createRoot(el: Element): { render(node: unknown): void };
}
declare module "react/jsx-runtime" {
  export const Fragment: unknown;
  export function jsx(type: unknown, props: unknown, key?: unknown): unknown;
  export function jsxs(type: unknown, props: unknown, key?: unknown): unknown;
}
declare namespace JSX { interface IntrinsicElements { [key: string]: any } }
