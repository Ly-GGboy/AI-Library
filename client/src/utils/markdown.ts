import MarkdownIt from 'markdown-it'
import type { Options } from 'markdown-it'
import Token from 'markdown-it/lib/token'

// 创建 markdown-it 实例
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
} as Options)

// 重写图片渲染规则
md.renderer.rules.image = (tokens: Token[], idx: number, options: Options, env: any, self: any): string => {
  const token = tokens[idx]
  const srcIndex = token.attrIndex('src')
  const src = token.attrs?.[srcIndex]?.[1] || ''
  const alt = token.content || ''
  
  // 构建图片标签，不包含文件名显示
  return `<img src="${src}" alt="${alt}" loading="lazy" decoding="async" class="markdown-image">`
}

// 移除图片后的文件名段落
const defaultParagraphRule = md.renderer.rules.paragraph_open || ((tokens: Token[], idx: number, options: Options, env: any, self: any) => self.renderToken(tokens, idx, options))

md.renderer.rules.paragraph_open = (tokens: Token[], idx: number, options: Options, env: any, self: any): string => {
  const nextToken = tokens[idx + 1]
  
  // 如果这个段落只包含一个图片文件名，就跳过渲染
  if (nextToken && 
      nextToken.type === 'inline' && 
      nextToken.children && 
      nextToken.children.length === 1 && 
      nextToken.children[0].type === 'text' && 
      (nextToken.children[0].content.endsWith('.png') || 
       nextToken.children[0].content.endsWith('.jpg') ||
       nextToken.children[0].content.endsWith('.jpeg') ||
       nextToken.children[0].content.endsWith('.gif') ||
       nextToken.children[0].content.endsWith('.webp'))) {
    return ''
  }
  
  return defaultParagraphRule(tokens, idx, options, env, self)
}

export default md 