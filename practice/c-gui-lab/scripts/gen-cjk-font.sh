# 从黑体重新生成界面中文字体（文本变更后重跑，产物 font_cn_*.c 进版本库）。
# 需要 node；走 npmmirror registry 避免网络问题。
npx --registry=https://registry.npmmirror.com -y lv_font_conv@1 --font "C:/Windows/Fonts/simhei.ttf" --size 20 --bpp 4 --format lvgl --no-compress --lv-font-name font_cn_20 -r 0x20-0x7f,0xb7,0x2014 --symbols "动画驱动的观感让透明度与光晕一起呼吸属性就是界面仪表控件实时图表自动同步亮暗" -o "$(dirname "$0")/../apps/lvgl-style/font_cn_20.c"
npx --registry=https://registry.npmmirror.com -y lv_font_conv@1 --font "C:/Windows/Fonts/simhei.ttf" --size 28 --bpp 4 --format lvgl --no-compress --lv-font-name font_cn_28 -r 0x20-0x7f,0xb7,0x2014 --symbols "动画驱动的观感让透明度与光晕一起呼吸属性就是界面仪表控件实时图表自动同步亮暗" -o "$(dirname "$0")/../apps/lvgl-style/font_cn_28.c"
