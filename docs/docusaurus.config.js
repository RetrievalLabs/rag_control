// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'rag_control',
  tagline: 'Runtime Governance, Security, and Execution Control for RAG Systems',

  // Set the production url of your site here
  url: 'https://rag-control.retrievallabs.ai',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'RetrievalLabs',
  projectName: 'rag_control',

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  // Favicon - same as logo
  favicon: 'img/favicon.svg',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is in Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          editUrl: 'https://github.com/RetrievalLabs/rag_control/tree/main/docs/',
          routeBasePath: '/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: true,
      },
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'rag_control',
        logo: {
          alt: 'rag_control Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Docs',
          },
          {
            href: 'https://github.com/RetrievalLabs/rag_control',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Getting Started',
                to: '/getting-started/quick-start',
              },
              {
                label: 'Core Concepts',
                to: '/concepts/overview',
              },
              {
                label: 'Architecture',
                to: '/architecture/overview',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/RetrievalLabs/rag_control',
              },
              {
                label: 'Issues',
                href: 'https://github.com/RetrievalLabs/rag_control/issues',
              },
            ],
          },
          {
            title: 'Company',
            items: [
              {
                label: 'RetrievalLabs',
                href: 'https://retrievallabs.ai',
              },
              {
                label: 'License',
                to: '/license',
              },
            ],
          },
        ],
        copyright: `Copyright © 2026 RetrievalLabs Co. All rights reserved.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['python', 'yaml', 'bash', 'json'],
      },
    }),
};

module.exports = config;
