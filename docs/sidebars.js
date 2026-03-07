/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    {
      type: 'doc',
      id: 'index',
      label: 'Home',
    },
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/configuration',
      ],
    },
    {
      type: 'category',
      label: 'Core Concepts',
      items: [
        'concepts/overview',
        'concepts/policies',
        'concepts/governance',
        'concepts/filters',
        'concepts/adapters',
      ],
    },
    {
      type: 'category',
      label: 'Observability',
      items: [
        'observability/audit-logging',
        'observability/distributed-tracing',
        'observability/metrics',
      ],
    },
    {
      type: 'category',
      label: 'Adapters',
      items: [
        'adapters/openai-adapter',
        'adapters/pinecone-adapter',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/engine',
        'api/policy-gov-config',
        'api/exceptions',
        'api/models',
        'api/adapters',
      ],
    },
    {
      type: 'doc',
      id: 'license',
      label: 'License',
    },
  ],
};

module.exports = sidebars;
