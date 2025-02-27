/// <reference types="vite/client" />

// 声明模块
declare module 'gsap' {
  export const gsap: any;
  export function to(target: any, vars: any): any;
  export function from(target: any, vars: any): any;
  export function fromTo(target: any, fromVars: any, toVars: any): any;
  export default {
    to,
    from,
    fromTo
  };
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 声明AnnouncementStore的类型
declare interface UpdateItem {
  id: string;
  title: string;
  description: string;
  date: string;
  changes?: string[];
  important?: boolean;
}

declare interface RecommendationItem {
  id: string;
  title: string;
  description: string;
  category: string;
  tags: string[];
  path?: string;
  url?: string;
}

declare interface FeedbackItem {
  name: string;
  type: string;
  content: string;
  contact: string;
  timestamp: string;
}
