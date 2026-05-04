import {
  buildInteractionDetail,
  buildInteractionSummary,
} from '../support/mockApi';

describe('Agent Call Detail', () => {
  it('renders coaching and llm insights for an unresolved call', () => {
    cy.visitAs('agent', '/agent/calls/int-002');

    cy.wait('@getInteractionDetail');
    cy.contains('Coaching Points').should('be.visible');
    cy.contains(/Hold Time Limit|Escalation Policy/).should('be.visible');
    cy.contains('LLM Coaching Insights').scrollIntoView().should('be.visible');
    cy.contains('Needs follow-up').should('exist');
    cy.contains('Contradiction').should('exist');
  });

  it('shows cached llm insights without exposing a refresh action', () => {
    cy.visitAs('agent', '/agent/calls/int-001');
    cy.wait('@getInteractionDetail');
    cy.contains('Account Login').should('be.visible');

    cy.contains('LLM Coaching Insights').should('be.visible');
    cy.get('[data-cy="llm-refresh"]').should('not.exist');
  });

  it('shows an unavailable state when llm insights are offline', () => {
    cy.visitAs('agent', '/agent/calls/int-001', {
      interactionDetails: {
        'int-001': {
          body: buildInteractionDetail(buildInteractionSummary(), {
            llmTriggers: {
              available: false,
              error: 'LLM offline',
              interactionId: 'int-001',
            } as any,
          }),
        },
      },
    });

    cy.wait('@getInteractionDetail');
    cy.contains('LLM coaching insights unavailable.').should('be.visible');
    cy.contains('LLM offline').should('be.visible');
  });

  it('shows an error state when the call detail request fails', () => {
    cy.visitAs('agent', '/agent/calls/int-500', {
      interactionDetails: {
        'int-500': {
          statusCode: 500,
        },
      },
    });

    cy.wait('@getInteractionDetail');
    cy.contains('Failed to load call details').should('be.visible');
  });

  it('renders emotion comparison panel with charts and alerts', () => {
    cy.visitAs('agent', '/agent/calls/int-003', {
      interactionDetails: {
        'int-003': {
          body: buildInteractionDetail(buildInteractionSummary(), {
            emotionComparison: {
              totalUtterances: 42,
              distributions: {
                acoustic: [
                  { emotion: 'neutral', count: 20, pct: 48 },
                  { emotion: 'angry', count: 12, pct: 28 },
                ],
                text: [
                  { emotion: 'neutral', count: 25, pct: 59 },
                  { emotion: 'frustrated', count: 5, pct: 12 },
                ],
                fused: [
                  { emotion: 'neutral', count: 22, pct: 52 },
                  { emotion: 'angry', count: 8, pct: 19 },
                ],
              },
              quality: {
                acousticTextAgreementRate: 45, // Poor, should trigger alert
                fusedMatchesAcousticRate: 85,
                fusedMatchesTextRate: 75,
                disagreementCount: 5,
              },
            },
          }),
        },
      },
    });

    cy.wait('@getInteractionDetail');
    
    // Check metric gauges
    cy.contains('Acoustic ↔ Text').scrollIntoView().should('be.visible');
    
    // Check charts section
    cy.contains('Emotion Distribution').should('be.visible');

    // Check alert section
    cy.contains('Cross-Modal Disagreement').should('be.visible');
    cy.contains('5 utterances show mismatch between acoustic and text emotions').should('be.visible');
  });
});
