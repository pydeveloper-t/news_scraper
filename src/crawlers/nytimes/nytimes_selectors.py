class NYTimesSelectors:
    SELECTORS_SETUP = {
        'ACCOUNT': '//button[contains(., "Account")]',
        'ACCEPT_ALL': '(//button[contains(@class, "fides-accept-all-button")])[1]',
        'UPDATE_TERMS': '#complianceOverlay button'
    }

    SELECTORS_COOKIES = {
        'ACCEPT_FRAME': '//div[contains(@id, "transcend-consent-manager")]',
        'ACCEPT_ALL': 'button>span.button-base-text.button-primary-text'
    }


    SELECTORS_LOGIN = {
        'ACCOUNT': '//button[@aria-label="Account Information"]/span[.="Account"]',
        'LOG_IN': '//a/span[text()="Log in"]',
        'EMAIL': '//input[@id="email"]',
        'EMAIL_CONTINUE': '//button[text()="Continue"]',
        'PASSWORD': '//input[@id="password"]',
        'LOGIN_BUTTON': '//button[@type="submit"]',
        'WITHOUT_SUBSCRIBING': '//a[text()="Continue without subscribing"]'        
    }


    SELECTORS_PAGE = {
        "DEFAULT": {
            # 'ARTICLE_TITLE': '//article[@id="story"]//h1[@data-testid="headline"]',
            'ARTICLE_TITLE': '(//main//h1)[1]',
            'ARTICLE_AUTHORS_LIST': '//span[@class="byline-prefix" and starts-with(text(), "By")]/following-sibling::a',
#            'ARTICLE_AUTHORS_ALTERNATIVE_LIST': '//div[@class="bottom-of-article"]//p/span[1]/a',
            'ARTICLE_CREATED': '(//time/@datetime)[1]',
            'ARTICLE_SUMMARY': '//article[@id="story"]//p[@id="article-summary"]',
            'ARTICLE_IMAGES_LIST': '//article[@id="story"]//div[@data-testid="imageblock-wrapper"]//picture//img/@src',
            'ARTICLE_IMAGE_CAPTION': '(//article[@id="story"]//div[@data-testid="imageblock-wrapper"]//figcaption/span)[1]',
            'ARTICLE_BODY': '//article[@id="story"]//section[@name="articleBody"]//p'
        },
        'WIRECUTTER': {},
        'INTERACTIVE': {
            'ARTICLE_TITLE': '(//main//h1)[1]',
            'ARTICLE_AUTHORS_LIST': '',
        },
        'ATHLETIC': {
            'ARTICLE_TITLE': '(//main//h1)[1]',
            'ARTICLE_AUTHORS_LIST': '//p[@id="writerBioText"]//a[contains(@href, "author")]',
            'ARTICLE_CREATED': '//span[@id="articleByLineString"]/following-sibling::div/',
            'ARTICLE_IMAGES_LIST': '(//div[@id="body-container"]//img)[1]/@src',
            'ARTICLE_BODY_LIST': '//div[@id="article-container-grid"]//p'
        },
    }