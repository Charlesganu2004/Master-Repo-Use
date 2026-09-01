/* Browser build of d19-code-cinema.jsx. No JSX runtime or network is required. */
'use strict';

function AtlasElement(tag, props) {
  return { tag, props: props || {} };
}

const codeCinema = AtlasElement('atlas-design', { option: 'cinema', source: 'JSX' });
AtlasNext.boot(codeCinema.props.option);
