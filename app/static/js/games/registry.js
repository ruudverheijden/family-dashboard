/** Each renderer mounts one server-owned board and returns its cleanup function. */
import * as memory from './memory.js';
import * as orchestra from './orchestra.js';
import * as maze from './maze.js';

export const games = { memory, orchestra, maze };
