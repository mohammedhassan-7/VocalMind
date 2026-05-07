import { buildInteractionDetail, buildInteractionSummary } from '../support/mockApi';

describe("Session Detail", () => {
  beforeEach(() => {
    // Intercept audio fetch to resolve instantly so the player renders
    cy.intercept('GET', '**/api/v1/interactions/*/audio', {
      statusCode: 200,
      body: new Blob([''], { type: 'audio/wav' }),
    }).as('getAudio');

    cy.visitAs("manager", "/manager/inspector/int-001", {
      interactionDetails: {
        'int-001': {
          body: buildInteractionDetail(buildInteractionSummary(), {
            emotionComparison: { 
              totalUtterances: 5,
              distributions: { acoustic: [], text: [], fused: [] },
              quality: { acousticTextAgreementRate: 0, fusedMatchesAcousticRate: 0, fusedMatchesTextRate: 0, disagreementCount: 0 }
            } as any, // Triggers hasEmotion
            policyViolations: [{ id: '1', policyName: 'Test' } as any], // Triggers hasViolations
            ragCompliance: { available: true } as any, // Triggers hasRag
          })
        }
      }
    });
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

  it("displays the score grid with four categories and trend icons", () => {
    cy.contains("Empathy");
    cy.contains("Policy");
    cy.contains("Resolution");
    cy.contains("Response Time");
    
    // The "Overall" score was removed from the grid, it's only in the ScoreRing
    // We check for the visual SVGs that represent trends
    cy.get('svg.lucide-trending-up, svg.lucide-trending-down, svg.lucide-minus').should('exist');
  });

  it("renders the SectionNav with auto-hiding tabs", () => {
    // The SectionNav appears between the header and the content
    cy.get('nav[aria-label="Session detail sections"]').should('exist');
    cy.contains("button", "Overview");
    cy.contains("button", "Transcript");
    cy.contains("button", "Emotion");
    cy.contains("button", "Violations");
    cy.contains("button", "Compliance");
    cy.contains("button", "LLM Analysis");
  });

  it("renders the audio player with an accessible input range", () => {
    cy.wait('@getAudio');
    cy.get('input[type="range"][aria-label="Seek recording position"]').should('exist');
    cy.get('button[aria-label="Play recording"]').should('exist');
    cy.get('button[aria-label="Mute recording"]').should('exist');
    cy.get('button[aria-label="Skip back 10 seconds"]').should('exist');
    cy.get('button[aria-label="Skip forward 10 seconds"]').should('exist');
  });

  it("renders the transcript section with utterances", () => {
    cy.get('#section-transcript').should('exist');
    cy.contains("Good morning! Thank you for calling VocalMind support.");
    cy.contains("Hi, I've been having issues with my account login");
  });

  it("renders emotion events section", () => {
    cy.get('#section-emotion').should('exist');
    cy.contains("Emotion Events");
  });

  it("renders automated evaluation cards", () => {
    cy.contains("h3", "Automated Evaluation");
    cy.contains("Process Adherence");
    cy.contains("Policy Inference");
  });

  it("renders ManagerAnnotation component instead of dispute flow", () => {
    // The dispute button is replaced with ManagerAnnotation flow
    cy.contains("Dispute").should("not.exist");
    
    // Find the Add annotation button for an emotion event or policy violation
    cy.contains("button", "Add annotation").first().click();
    
    // Manager feedback buttons should appear
    cy.contains("button", "Yes, accurate").should("be.visible");
    cy.contains("button", "No, inaccurate").should("be.visible");
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
            emotionComparison: { 
              totalUtterances: 5,
              distributions: { acoustic: [], text: [], fused: [] },
              quality: { acousticTextAgreementRate: 0, fusedMatchesAcousticRate: 0, fusedMatchesTextRate: 0, disagreementCount: 0 }
            } as any, // Triggers hasEmotion
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

    // Check tabs
    cy.contains("button", "Policy Findings").should("be.visible");
    cy.contains("button", "Span-Level Trigger Attribution").should("be.visible");

    // Check verdicts
    cy.contains("Supported").should("be.visible");
    
    // Switch to Emotion tab to see Cross-Modal Mismatch
    cy.contains("button", "Span-Level Trigger Attribution").click();
    cy.contains("Cross-Modal Mismatch").should("be.visible");
  });
});
