from regular_expression import RegexInterpreter

engine = RegexInterpreter(r"\d+")

print(engine.visualize())
print(engine.generate_transition_table())
