// 极简行内格式(ADR 0058):**加粗** 与 `代码`,渲染成 Vue 片段。
import { h, type PropType } from "vue";

export const InlineText = {
  props: { text: { type: String as PropType<string | undefined>, default: "" } },
  setup(props: { text?: string }) {
    return () => {
      const parts: (string | ReturnType<typeof h>)[] = [];
      const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
      const source = props.text ?? "";
      let last = 0;
      let key = 0;
      let m: RegExpExecArray | null;
      while ((m = re.exec(source)) !== null) {
        if (m.index > last) parts.push(source.slice(last, m.index));
        const token = m[0];
        if (token.startsWith("**")) {
          parts.push(h("strong", { key: key++ }, token.slice(2, -2)));
        } else {
          parts.push(h("code", { key: key++ }, token.slice(1, -1)));
        }
        last = m.index + token.length;
      }
      if (last < source.length) parts.push(source.slice(last));
      return parts;
    };
  },
};
