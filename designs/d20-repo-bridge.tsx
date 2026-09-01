/** @jsx AtlasElement */
/** Authored TSX source. It compiles to the dependency-free JavaScript sibling. */
type BridgeOption = 'bridge';

interface AtlasElementResult {
  tag: string;
  props: { option: BridgeOption; source: 'TSX' };
}

declare namespace JSX {
  interface Element extends AtlasElementResult {}
  interface IntrinsicElements {
    'atlas-design': AtlasElementResult['props'];
  }
}

declare const AtlasNext: { boot(option: BridgeOption): void };

function AtlasElement(tag: string, props: AtlasElementResult['props']): AtlasElementResult {
  return { tag, props };
}

const repoBridge = <atlas-design option="bridge" source="TSX" />;
AtlasNext.boot(repoBridge.props.option);
