import { buildInteractionDetail, buildInteractionSummary } from '../support/mockApi';

describe("Session Detail", () => {
  beforeEach(() => {
    cy.visitAs("manager", "/manager/inspector/int-001");
  });

  it("renders the back navigation link", () => {
    cy.contains("a", "Back to Session Inspector")
      .should("have.attr", "href", "/manager/inspector");
  });

  it("displays agent name and call metadata", () => {
    cy.contains("h2", "Sarah M.");
    cy.contains(/english/i);
    cy.contains("2025-03-01");
    cy.contains("09:15 AM");
  });

  it("displays the score grid with four categories", () => {
    cy.contains("Empathy");
    cy.contains("Policy");
    cy.contains("Resolution");
    cy.contains("Resp. Time");
  });

  it("renders the transcript section with utterances", () => {
    cy.contains("h3", "Transcript");
    cy.contains("Good morning! Thank you for calling VocalMind support.");
    cy.contains("Hi, I've been having issues with my account login");
  });

  it("renders emotion events section", () => {
    cy.contains("Emotion Events");
    cy.contains("Agent");
    cy.contains("Customer");
    cy.contains("Jump to");
  });

  it("renders automated evaluation cards", () => {
    cy.contains("h3", "Automated Evaluation");
    cy.contains("Process Adherence");
    cy.contains("Policy Inference");
  });

  it("renders emotion trigger reasoning card", () => {
    cy.contains("h4", "Emotion Trigger Reasoning");
    cy.contains("Dissonance:");
    cy.contains("Counterfactual:");
  });

  it("navigates back to session inspector", () => {
    cy.contains("a", "Back to Session Inspector").click();
    cy.url().should("include", "/manager/inspector");
    cy.url().should("not.include", "/int-001");
  });

  it("renders Evidence-Anchored Explainability with tabs and badges", () => {
    // Visit with mock data containing explainability
    cy.visitAs("manager", "/manager/inspector/int-002", {
      interactionDetails: {
        'int-002': {
          body: buildInteractionDetail(buildInteractionSummary(), {
            llmTriggers: {
              available: true,
              explainability: {
                triggerAttributions: [
                  {
                    attributionId: "attr-1",
                    triggerType: "policy_finding",
                    title: "Missing Identity Verification",
                    reasoning: "Agent did not verify account.",
                    verdict: "Supported",
                    family: "policy",
                    evidenceChain: [],
                    supportingQuotes: [],
                  },
                  {
                    attributionId: "attr-2",
                    triggerType: "cross_modal_fusion",
                    title: "Text/Acoustic Mismatch",
                    reasoning: "Customer sounded angry but text was neutral.",
                    verdict: "Cross-Modal Mismatch",
                    family: "emotion",
                    evidenceChain: [],
                    supportingQuotes: [],
                  }
                ],
                claimProvenance: []
              }
            } as any
          })
        }
      }
    });

    cy.wait('@getInteractionDetail');

    // Panel title
    cy.contains("Evidence-Anchored Explainability").scrollIntoView().should("be.visible");
    cy.contains("h3", "Claim to evidence to verdict").should("be.visible");

    // Check tabs (they are based on family types defined in mock)
    cy.contains("button", "Policy Findings").should("be.visible");
    cy.contains("button", "Span-Level Trigger Attribution").should("be.visible");

    // Check verdicts
    cy.contains("Supported").should("be.visible");
    
    // Switch to Emotion tab to see Cross-Modal Mismatch
    cy.contains("button", "Span-Level Trigger Attribution").click();
    cy.contains("Cross-Modal Mismatch").should("be.visible");
  });
});
