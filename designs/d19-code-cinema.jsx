/** @jsx AtlasElement */
/** Authored JSX source using a tiny local element factory; React is not required. */
function AtlasElement(tag, props) {
  return { tag, props: props || {} };
}

const codeCinema = <atlas-design option="cinema" source="JSX" />;
AtlasNext.boot(codeCinema.props.option);
