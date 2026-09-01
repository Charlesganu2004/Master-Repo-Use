/* Browser build of d20-repo-bridge.tsx. No TSX runtime or network is required. */
'use strict';

function AtlasElement(tag, props) {
  return { tag, props };
}

const repoBridge = AtlasElement('atlas-design', { option: 'bridge', source: 'TSX' });
AtlasNext.boot(repoBridge.props.option);
