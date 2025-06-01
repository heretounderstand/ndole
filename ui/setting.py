import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import random

def display_settings():
    st.title("🎲 Polynomialle")
    st.info("🚧 Quick heads up! The settings page is coming soon, but we've got something fun for you to try while you wait - dive into Polynomialle and test your math skills! 🧮✨")
    if 'polynomial_degree' not in st.session_state:
        st.session_state.polynomial_degree = random.randint(1, 9)
        st.session_state.coefficients = [random.randint(-10, 10) for _ in range(st.session_state.polynomial_degree + 1)]
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
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y, 'b-', linewidth=2)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    ax.set_xlabel('x')
    ax.set_ylabel('f(x)')
    ax.set_title('Mystery Polynomial')
    y_max = max(abs(np.min(y)), abs(np.max(y)))
    if y_max > 100:
        ax.set_ylim(-100, 100)
    st.pyplot(fig)
    plt.close()
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