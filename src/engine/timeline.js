/**
 * Timeline manager - drives scene transitions based on elapsed time.
 */

export const SCENES = {
  LAUNCHPAD:  { id: 'launchpad',  start: 0,    end: 3    },
  LIFTOFF:    { id: 'liftoff',    start: 3,    end: 10   },
  ASCENT:     { id: 'ascent',     start: 10,   end: 15   },
  SEPARATION: { id: 'separation', start: 15,   end: 19   },
  RETURN:     { id: 'return',     start: 19,   end: 26   },
  CATCH:      { id: 'catch',      start: 26,   end: 31   },
  FINALE:     { id: 'finale',     start: 31,   end: 34   },
};

export const TOTAL_DURATION = 34;

const sceneList = Object.values(SCENES);

export class Timeline {
  constructor() {
    this.globalTime = 0;
    this.currentScene = null;
    this.sceneLocalTime = 0;
    this.sceneProgress = 0; // 0..1 within current scene
    this.finished = false;
  }

  /**
   * Update timeline with elapsed seconds.
   */
  update(globalTime) {
    this.globalTime = globalTime;

    if (globalTime >= TOTAL_DURATION) {
      this.finished = true;
      this.currentScene = sceneList[sceneList.length - 1];
      this.sceneLocalTime = this.currentScene.end - this.currentScene.start;
      this.sceneProgress = 1;
      return;
    }

    for (const scene of sceneList) {
      if (globalTime >= scene.start && globalTime < scene.end) {
        this.currentScene = scene;
        this.sceneLocalTime = globalTime - scene.start;
        this.sceneProgress = this.sceneLocalTime / (scene.end - scene.start);
        break;
      }
    }
  }

  /**
   * Check if we're currently in a specific scene.
   */
  isScene(sceneId) {
    return this.currentScene && this.currentScene.id === sceneId;
  }

  /**
   * Get the scene ID string.
   */
  getSceneId() {
    return this.currentScene ? this.currentScene.id : null;
  }
}
