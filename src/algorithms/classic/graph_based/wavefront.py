from typing import List, Tuple

import numpy as np

from algorithms.algorithm import Algorithm
from algorithms.basic_testing import BasicTesting
from algorithms.configuration.entities.agent import Agent
from algorithms.configuration.entities.goal import Goal
from algorithms.configuration.maps.map import Map
from simulator.services.services import Services
from simulator.views.map.display.gradient_map_display import GradientMapDisplay
from simulator.views.map.display.map_display import MapDisplay
from structures import Point, DynamicColour, Colour, BLUE
from structures.tracked_list import TrackedList
from structures.factory import gen_list


class Wavefront(Algorithm):
    step_grid: List[Tuple[int, Point]]
    step_grid_min_colour: DynamicColour
    step_grid_max_colour: DynamicColour

    def __init__(self, services: Services, testing: BasicTesting = None):
        super().__init__(services, testing)

        grid: Map = self._get_grid()
        ls: List[Tuple[int, Point]] = []
        for idx in np.ndindex(*grid.size):
            ls.append((0, Point(*idx)))
        self.step_grid = gen_list(self._services, ls)

        self.step_grid_min_colour = self._services.state.add_colour("step min", BLUE.with_alpha(0))
        self.step_grid_max_colour = self._services.state.add_colour("step max", BLUE)

        self.__map_displays = [GradientMapDisplay(self._services, pts=self.step_grid, min_colour=self.step_grid_min_colour, max_colour=self.step_grid_max_colour)]

    def set_display_info(self) -> List[MapDisplay]:
        """
        Read super description
        """
        return super().set_display_info() + self.__map_displays
    
    def __lin_idx(self, p: Point) -> int:
        return np.ravel_multi_index(p.values, self._get_grid().size)

    def _find_path_internal(self) -> None:
        """
        Read super description
        The internal implementation of :ref:`find_path`
        """
        # ._get_grid() is in Algorithm class and gets the map
        grid: Map = self._get_grid()
        # agent and goal are represented by a point(x,y) and radius
        agent: Agent = grid.agent
        goal: Goal = grid.goal
        # put position of goal in tuple with 2 in a list called queue -> queue= [(Point(x=??, y=??), 2)]
        queue: List[Tuple[Point, int]] = [(goal.position, 2)]
        # make all the cells of the step_grid 0
        for i in range(len(self.step_grid)):
            self.step_grid[i] = (0, self.step_grid[i][1])

        # make the goal cell 1
        goal_idx = self.__lin_idx(goal.position)
        self.step_grid[goal_idx] = (1, self.step_grid[goal_idx][1])

        # agent_reached is True when the agent position is equal to goal position
        agent_reached: bool = (goal.position == agent.position)

        while len(queue) > 0 and not agent_reached:
            next_node: Point
            count: int
            next_node, count = queue.pop(0)
            for n in grid.get_next_positions(next_node):
                n_idx = self.__lin_idx(n)
                if self.step_grid[n_idx][0] == 0:
                    self.step_grid[n_idx] = (count, self.step_grid[n_idx][1])
                    queue.append((n, count + 1))
                if n == agent.position:
                    agent_reached = True
                    self.step_grid[n_idx] = (count, self.step_grid[n_idx][1])
                    break
            self.key_frame()

        if agent_reached:
            trace: List[Point] = self.gradient_descent(agent.position, grid)
            for t in trace:
                self.move_agent(t)
                self.key_frame(ignore_key_frame_skip=True)

    def gradient_descent(self, current: Point, grid: Map) -> List[Point]:
        """
        Search backward from the given point the next lowest number until we reach the agent position
        :param current: The position from witch to start the descent
        :param grid: the map
        :return: The trace
        """
        trace: List[Point] = [current]
        # find the trace of the path by looking at neighbours at each point and moving the current towards the agent position. (number to next lowest numb(-1))
        while self.step_grid[self.__lin_idx(current)][0] != 1:
            for n in grid.get_next_positions(current):
                if self.step_grid[self.__lin_idx(n)][0] == self.step_grid[self.__lin_idx(current)][0] - 1:
                    trace.append(n)
                    current = n
                    break

        return trace[1:]
