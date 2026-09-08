/* Ambient declarations to satisfy TypeScript language server for reference React components */
declare module "react" {
  export function useState<T = any>(initialState?: T | (() => T)): [T, (action: T | ((prev: T) => T)) => void];
  export function useEffect(effect: () => void | (() => void), deps?: readonly any[]): void;
  export function useRef<T = any>(initialValue?: T): { current: T };
  export function useId(): string;
  export function useMemo<T = any>(factory: () => T, deps?: readonly any[]): T;
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps?: readonly any[]): T;
  export function forwardRef<T = any, P = any>(render: (props: P, ref: any) => any): any;
  export function createContext<T = any>(defaultValue: T): any;
  export function useContext<T = any>(context: any): T;
  export type ReactNode = any;
  export type FC<P = {}> = (props: P) => any;
  export type ComponentProps<T = any> = any;
  export type ComponentPropsWithoutRef<T = any> = any;
  export type ElementRef<T = any> = any;
  export type HTMLAttributes<T = any> = any;
  export type ButtonHTMLAttributes<T = any> = any;
  export type ElementType<P = any> = any;
  export type ComponentType<P = any> = any;
  export type Ref<T = any> = any;
  export type RefObject<T = any> = { current: T };
  export type ReactElement<P = any, T = any> = any;
  const React: {
    useState: typeof useState;
    useEffect: typeof useEffect;
    useRef: typeof useRef;
    useId: typeof useId;
    useMemo: typeof useMemo;
    useCallback: typeof useCallback;
    forwardRef: typeof forwardRef;
    createContext: typeof createContext;
    useContext: typeof useContext;
    [key: string]: any;
  };
  export default React;
}

declare namespace React {
  export type ReactNode = any;
  export type FC<P = {}> = (props: P) => any;
  export type ComponentProps<T = any> = any;
  export type ComponentPropsWithoutRef<T = any> = any;
  export type ElementRef<T = any> = any;
  export type HTMLAttributes<T = any> = any;
  export type ButtonHTMLAttributes<T = any> = any;
  export type SVGProps<T = any> = any;
  export type ElementType<P = any> = any;
  export type ComponentType<P = any> = any;
  export type Ref<T = any> = any;
  export type RefObject<T = any> = { current: T };
  export type ReactElement<P = any, T = any> = any;
  export function forwardRef<T = any, P = any>(render: (props: P, ref: any) => any): any;
  export function useState<T = any>(initialState?: T | (() => T)): [T, (action: T | ((prev: T) => T)) => void];
  export function useEffect(effect: () => void | (() => void), deps?: readonly any[]): void;
  export function useMemo<T = any>(factory: () => T, deps?: readonly any[]): T;
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps?: readonly any[]): T;
  export function useRef<T = any>(initialValue?: T): { current: T };
}

declare module "react/jsx-runtime" {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module "clsx" {
  export type ClassValue = any;
  export function clsx(...inputs: any[]): string;
  export default clsx;
}

declare module "tailwind-merge" {
  export function twMerge(...classLists: any[]): string;
}

declare module "class-variance-authority" {
  export function cva(base?: any, config?: any): any;
  export type VariantProps<T = any> = any;
}

declare module "@radix-ui/react-slot" {
  export const Slot: any;
  export const Slottable: any;
}

declare module "vaul" {
  export const Drawer: any;
  export default Drawer;
}

declare module "react-use-measure" {
  export default function useMeasure(options?: any): any;
}

declare module "motion/react" {
  export const motion: any;
  export const AnimatePresence: any;
}

declare module "framer-motion" {
  export const motion: any;
  export const AnimatePresence: any;
}

declare module "lucide-react";
declare module "@/*";

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

