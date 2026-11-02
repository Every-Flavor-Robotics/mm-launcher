CXX ?= c++
CXXFLAGS ?= -std=c++20 -Wall -Wextra -Werror -O1 -g -fsanitize=undefined
INC = -I../../components/hiwonder_bus/include -I../../main

all: run

test_hiwonder: test_hiwonder.cpp ../../components/hiwonder_bus/include/hiwonder_bus_board.hpp
	$(CXX) $(CXXFLAGS) $(INC) $< -o $@

test_joints: test_joints.cpp ../../main/joint_map.hpp
	$(CXX) $(CXXFLAGS) $(INC) $< -o $@

test_tip_guard: test_tip_guard.cpp ../../main/tip_guard.hpp
	$(CXX) $(CXXFLAGS) $(INC) $< -o $@

test_jsonf: test_jsonf.cpp ../../main/jsonf.hpp
	$(CXX) $(CXXFLAGS) $(INC) $< -o $@

test_stop_rule: test_stop_rule.cpp ../../main/stop_rule.hpp
	$(CXX) $(CXXFLAGS) $(INC) $< -o $@

run: test_hiwonder test_joints test_tip_guard test_jsonf test_stop_rule
	./test_hiwonder && ./test_joints && ./test_tip_guard && ./test_jsonf && ./test_stop_rule
	node test_gamepad.mjs

clean:
	rm -rf test_hiwonder test_joints test_tip_guard test_jsonf test_stop_rule *.dSYM

.PHONY: all run clean
