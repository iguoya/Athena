module.exports = {
  title: ' English Notebook',
  description: ' Practice and Writing ',
  base: '/',
//  dest: 'public',
  plugins: [
    ['autobar'],
  ],
  themeConfig: {
    nav: [
      {
        text: '首页',
        link: '/home/'
      },
      {
        text: 'H5',
        link: '/H5/'
      },
      {
        text: '规范',
        link: '/Standard/'
      }
    ],
    sidebar: [

    ]
  }
}
