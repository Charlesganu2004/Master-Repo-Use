/** Authored TypeScript source. The checked-in JavaScript sibling runs offline. */
type AtlasDesignOption = 'forge';

interface AtlasDesignRuntime {
  boot(option: AtlasDesignOption): void;
}

declare const AtlasNext: AtlasDesignRuntime;

const stackForge: Readonly<{ option: AtlasDesignOption; source: 'TypeScript' }> = {
  option: 'forge',
  source: 'TypeScript',
};

AtlasNext.boot(stackForge.option);
