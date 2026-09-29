function createPartyPlan() {

    const guests = Number(
        document.getElementById("guests").value
    );

    const partyType =
        document.getElementById("partyType").value;

    const budget = Number(
        document.getElementById("budget").value
    );

    const needs =
        document.getElementById("needs").value.trim();


    // VALIDATION
    if (!guests || guests <= 0) {

        alert("Please enter the number of guests.");

        return;
    }


    if (!budget || budget <= 0) {

        alert("Please enter your budget.");

        return;
    }


    // BUDGET BREAKDOWN
    const food = Math.round(budget * 0.40);

    const decoration = Math.round(budget * 0.25);

    const music = Math.round(budget * 0.15);

    const other =
        budget - food - decoration - music;


    // RESULT
    const result =
        document.getElementById("party-result");


    result.innerHTML = `

        <section class="result-card">

            <div class="result-header">

                <div>
                    <p class="result-label">
                        YOUR PARTY PLAN
                    </p>

                    <h2>
                        ${partyType} 🎉
                    </h2>
                </div>

                <div class="result-icon">
                    🎊
                </div>

            </div>


            <div class="party-details">

                <div class="detail-item">

                    <span>👥 Guests</span>

                    <strong>
                        ${guests}
                    </strong>

                </div>


                <div class="detail-item">

                    <span>🎪 Party Type</span>

                    <strong>
                        ${partyType}
                    </strong>

                </div>


                <div class="detail-item">

                    <span>💰 Total Budget</span>

                    <strong>
                        ₹${budget.toLocaleString("en-IN")}
                    </strong>

                </div>


                <div class="detail-item needs-item">

                    <span>📝 Needs</span>

                    <strong>
                        ${needs || "Not specified"}
                    </strong>

                </div>

            </div>


            <div class="budget-section">

                <h3>
                    💰 Budget Breakdown
                </h3>


                <div class="budget-list">


                    <div class="budget-row">

                        <div class="budget-name">
                            🍽️ Food
                        </div>

                        <div class="budget-amount">
                            ₹${food.toLocaleString("en-IN")}
                        </div>

                    </div>


                    <div class="budget-row">

                        <div class="budget-name">
                            🎈 Decoration
                        </div>

                        <div class="budget-amount">
                            ₹${decoration.toLocaleString("en-IN")}
                        </div>

                    </div>


                    <div class="budget-row">

                        <div class="budget-name">
                            🎵 Music
                        </div>

                        <div class="budget-amount">
                            ₹${music.toLocaleString("en-IN")}
                        </div>

                    </div>


                    <div class="budget-row">

                        <div class="budget-name">
                            ✨ Other
                        </div>

                        <div class="budget-amount">
                            ₹${other.toLocaleString("en-IN")}
                        </div>

                    </div>

                </div>

            </div>


            <div class="success-message">

                🎉 Your party plan is ready!

            </div>

        </section>

    `;
}