import random
import numpy as np
import plotly.graph_objects as go
import streamlit as st


def display_polynomialle():
    st.title("🎲 Polynomialle")
    st.caption("Guess the mystery polynomial from its curve and test your math skills! 🧮✨")
    if 'polynomial_degree' not in st.session_state:
        st.session_state.polynomial_degree = random.randint(1, 9)
        # The leading coefficient must be non-zero, otherwise the announced degree would be wrong.
        leading = random.choice([c for c in range(-10, 11) if c != 0])
        st.session_state.coefficients = [leading] + [random.randint(-10, 10) for _ in range(st.session_state.polynomial_degree)]
        st.session_state.attempts = 0
        st.session_state.max_attempts = 10
        st.session_state.guesses = []
        st.session_state.game_over = False
        st.session_state.won = False
    st.header(f"Guess the Polynomial of Degree {st.session_state.polynomial_degree}")
    st.write(f"You have {st.session_state.max_attempts - st.session_state.attempts} attempts remaining")
    x = np.linspace(-3, 3, 1000)
    y = np.zeros_like(x)
    for i, coeff in enumerate(st.session_state.coefficients):
        power = st.session_state.polynomial_degree - i
        y += coeff * (x ** power)
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines", line=dict(width=3)))
    fig.update_layout(title="Mystery Polynomial", xaxis_title="x", yaxis_title="f(x)", height=420,
                      margin=dict(l=20, r=20, t=50, b=20))
    if np.max(np.abs(y)) > 100:
        fig.update_yaxes(range=[-100, 100])
    st.plotly_chart(fig, width="stretch")
    polynomial_str = "f(x) = "
    for i in range(st.session_state.polynomial_degree + 1):
        power = st.session_state.polynomial_degree - i
        if power == 0:
            polynomial_str += "? "
        elif power == 1:
            polynomial_str += "?x "
        else:
            polynomial_str += f"?x^{power} "
        if i < st.session_state.polynomial_degree:
            polynomial_str += "+ "
    st.write(f"**Target polynomial structure:** {polynomial_str}")
    if not st.session_state.game_over:
        st.subheader("Make Your Guess")
        guess_coeffs = []
        cols = st.columns(st.session_state.polynomial_degree + 1)
        for i, col in enumerate(cols):
            power = st.session_state.polynomial_degree - i
            if power == 0:
                label = "Constant"
            elif power == 1:
                label = "x coeff"
            else:
                label = f"x^{power} coeff"
            with col:
                coeff = st.number_input(
                    label,
                    min_value=-10,
                    max_value=10,
                    value=st.session_state.guesses[st.session_state.attempts - 1][0][i] if st.session_state.attempts else 0,
                    key=f"coeff_{i}_{st.session_state.attempts}"
                )
                guess_coeffs.append(coeff)
        if st.button("Submit Guess", type="primary"):
            st.session_state.attempts += 1
            feedback = []
            for i, (guess, actual) in enumerate(zip(guess_coeffs, st.session_state.coefficients)):
                if guess == actual:
                    feedback.append("correct")
                elif guess < actual:
                    feedback.append("too_low")
                else:
                    feedback.append("too_high")
            st.session_state.guesses.append((guess_coeffs.copy(), feedback.copy()))
            if all(f == "correct" for f in feedback):
                st.session_state.won = True
                st.session_state.game_over = True
            elif st.session_state.attempts >= st.session_state.max_attempts:
                st.session_state.game_over = True
    if st.session_state.guesses:
        st.subheader("Your Guesses")
        for attempt_num, (guess, feedback) in enumerate(st.session_state.guesses, 1):
            st.write(f"**Attempt {attempt_num}:**")
            cols = st.columns(len(guess))
            for i, (coeff, fb) in enumerate(zip(guess, feedback)):
                with cols[i]:
                    if fb == "correct":
                        st.success(f"{coeff} ✓")
                    elif fb == "too_low":
                        st.error(f"{coeff} ↑")
                    else:
                        st.warning(f"{coeff} ↓")
    if st.session_state.game_over:
        if st.session_state.won:
            st.success("🎉 Congratulations! You guessed the polynomial correctly!")
        else:
            st.error("😔 Game Over! You've used all your attempts.")
        st.subheader("The Answer")
        answer_str = "f(x) = "
        for i, coeff in enumerate(st.session_state.coefficients):
            power = st.session_state.polynomial_degree - i
            if i > 0 and coeff >= 0:
                answer_str += " + "
            elif i > 0:
                answer_str += " "
            if power == 0:
                answer_str += str(coeff)
            elif power == 1:
                if coeff == 1:
                    answer_str += "x"
                elif coeff == -1:
                    answer_str += "-x"
                else:
                    answer_str += f"{coeff}x"
            else:
                if coeff == 1:
                    answer_str += f"x^{power}"
                elif coeff == -1:
                    answer_str += f"-x^{power}"
                else:
                    answer_str += f"{coeff}x^{power}"
        st.code(answer_str)
        if st.button("Play Again", type="primary"):
            for key in ['polynomial_degree', 'coefficients', 'attempts', 'guesses', 'game_over', 'won']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    st.subheader("Legend")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("✓ Correct coefficient")
    with col2:
        st.error("↑ Your guess is too low")
    with col3:
        st.warning("↓ Your guess is too high")