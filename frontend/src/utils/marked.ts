import { marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// 代码块语法高亮（模块级只执行一次，切勿移到组件内部）
marked.use(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value
        } catch (e) {
          console.error('高亮失败：', e)
        }
      }
      return hljs.highlightAuto(code).value
    }
  })
)

export { marked }