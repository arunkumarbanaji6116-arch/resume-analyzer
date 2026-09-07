/* Ambient declarations to satisfy TypeScript language server for reference React components */
declare module "react" {
  export const useState: <T>(initialState: T | (() => T)) => [T, (newState: T | ((prevState: T) => T)) => void];
  export const useEffect: (effect: () => void | (() => void), deps?: readonly any[]) => void;
  export type ReactNode = any;
  export type FC<P = {}> = (props: P) => any;
  const React: any;
  export default React;
}

declare module "react/jsx-runtime" {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module "lucide-react" {
  export const Home: any;
  export const FileText: any;
  export const Mic: any;
  export const Compass: any;
  export const Briefcase: any;
  export const ChevronDown: any;
  export const ChevronsRight: any;
  export const Moon: any;
  export const Sun: any;
  export const TrendingUp: any;
  export const Activity: any;
  export const Award: any;
  export const Bell: any;
  export const Settings: any;
  export const HelpCircle: any;
  export const User: any;
  export const ShoppingCart: any;
  export const Tag: any;
  export const BarChart3: any;
  export const Users: any;
  export const Package: any;
  const icons: Record<string, any>;
  export default icons;
}

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

