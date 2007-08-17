<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="html" encoding="iso-8859-1"/> 
<xsl:template match="/">

<html> <!-- xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" > -->
  <head>
    <style type="text/css">

      body
      {
      background: #000000;
      color: #AAAAAA;
      margin: 0
      }

      div#crypt
      {
      background: #000000;
      }

      div#info
      {
      background: #331111;
      width: 100%;
      }

      div#library
      {
      background: #000000
      url("http://www.white-wolf.com/VTES/images/CardsImg.jpg")
      no-repeat scroll top right;
      }

      div#cardtext
      {
      background: #000000
      }

      div#cardtext h4
      {
      text-decoration: underline;
      }

      div#cardtext h5
      {
      font-weight: normal;
      text-decoration: underline;
      margin-left: 1em;
      margin-bottom: 0.1em;
      }

      div#cardtext div.text
      {
      margin-left: 1em;
      }

      div#cardtext ul
      {
      list-style-type: none;
      margin-top: 0.1em;
      margin-bottom: 0.1em;
      padding-left: 1em;
      }

      div#cardtext .label
      {
      font-style: italic;
      }

      h1
      {
      font-size: x-large;
      margin-left: 1cm
      }

      h2
      {
      font-size: large;
      margin-left: 1cm
      }

      h3
      {
      font-size: large;
      border-bottom: solid;
      border-width: 2px;
      }

      h4
      {
      font-size: medium;
      margin-bottom: 0px
      }

      table
      {
      line-height: 70%
      }

      .generator
      {
      color: #555555;
      position: relative;
      top: 20px;
      }

      .taunt
      {
      color: #111111;
      position: relative;
      top: 20px;
      }

      .requirement
      {
      font-style:italic
      }

      .librarytype
      {

      }

      .stats
      {
      color: #777777;
      margin: 5px;
      }

      .tablevalue
      {
      color: #aaaa88;
      margin: 5px
      }

      .value
      {
      color: #aaaa88
      }

      hr {color: sienna}

      p {margin-left: 60px}

      a
      {
      color: #aaaa88;
      margin: 5px;
      text-decoration: none
      }

      a:hover
      {
      color: #ffffff;
      margin: 5px;
      text-decoration: none
      }
    </style>
    <title>VTES deck : <xsl:value-of select="deck/name"/> by <xsl:value-of select="deck/author"/></title>
  </head>
  <body>
    <div id="info">
      <h1 id="nametitle"><span>Deck Name : </span><span class="value" id="namevalue"><xsl:value-of select="deck/name"/></span></h1>
      <h2 id="authortitle"><span>Author : </span><span class="value" id="authorvalue"><xsl:value-of select="deck/author"/></span></h2>
      <h2 id="descriptiontitle"><span>Description : </span></h2>
      <p id="description"><span class="value" id="descriptionvalue">
      <xsl:call-template name="line-breaks">
        <xsl:with-param name="text" select="string(deck/description)" />
      </xsl:call-template>
      </span></p>
    </div>

    <div id="crypt">
      <h3 id="crypttitle"><span>Crypt </span><span class="stats"
      id="cryptstats">[<xsl:value-of select="deck/crypt/@size"/>
      vampires] Capacity min : <xsl:value-of select="deck/crypt/@min"/>
      max : <xsl:value-of select="deck/crypt/@max"/> average : <xsl:value-of select="deck/crypt/@avg"/></span></h3>

      <div class="crypttable" id="crypttable">
        <table><tbody>
        <xsl:for-each select="/deck/crypt/vampire[not(name=preceding-sibling::vampire/name)]">
          <xsl:sort select="@count" data-type="number" order="descending"/>
	  <xsl:sort select="capacity" data-type="number" order="descending"/>
          <xsl:sort select="name"/>
	    <xsl:variable name="xname" select="string(name)"/>
	    <xsl:for-each select="/deck/crypt/vampire[name=$xname and not(adv=preceding-sibling::vampire[name=$xname]/adv)]">
              <tr>
                <td><span class="tablevalue"><xsl:call-template name="count-vampires"><xsl:with-param name="myname" select="string(name)" /><xsl:with-param name="myadv" select="string(adv)" /></xsl:call-template>x</span></td>
                <td><span class="tablevalue"><a><xsl:attribute name='href'>http://monger.vekn.org/showvamp.html?NAME=<xsl:value-of select="name"/><xsl:if test="adv!=''">  ADV</xsl:if></xsl:attribute><xsl:value-of select="name"/></a></span></td>
                <td><span class="tablevalue"><xsl:value-of select="adv"/></span></td>
                <td><span class="tablevalue"><xsl:value-of select="capacity"/></span></td>
                <td><span class="tablevalue"><xsl:value-of select="disciplines"/></span></td>
                <td><span class="tablevalue"><xsl:value-of select="title"/></span></td>
	        <td><span class="tablevalue"><xsl:value-of select="clan"/> (group <xsl:value-of select="group"/>)</span></td>
	      </tr>
	    </xsl:for-each>
        </xsl:for-each>
      </tbody></table>
      </div>
    </div>


    <div id="library">
      <h3 id="librarytitle"><span>Library </span><span class="stats" id="librarystats">[<xsl:value-of select="deck/library/@size"/> cards]</span></h3>

      <xsl:for-each select="/deck/library/card[not(type=preceding-sibling::card/type)]">
        <xsl:sort select="type"/>
        <xsl:call-template name="LIBPART">
          <xsl:with-param name="mytype" select="string(type)" />
        </xsl:call-template>
      </xsl:for-each>
    </div>

    <div id="cardtext">
       <h3 class="cardtext"><span>Card Texts </span></h3>

       <h4 class="librarytype">Crypt</h4>

       <xsl:for-each select="/deck/crypt/vampire[not(name=preceding-sibling::vampire/name)]">
         <xsl:sort select="@count" data-type="number" order="descending"/>
	     <xsl:sort select="capacity" data-type="number" order="descending"/>
         <xsl:sort select="name"/>
	     <xsl:variable name="xname" select="string(name)"/>
	     <xsl:for-each select="/deck/crypt/vampire[name=$xname and not(adv=preceding-sibling::vampire[name=$xname]/adv)]">
           <h5 id="cardname"><xsl:value-of select="name"/></h5>
           <ul>
             <li><span class="label">Capacity</span>: <span class="capacity"><xsl:value-of select="capacity"/></span></li>
             <li><span class="label">Group</span>: <span class="group"><xsl:value-of select="group"/></span></li>
             <li><span class="label">Clan</span>: <span class="clan"><xsl:value-of select="clan"/></span></li>
             <li><span class="label">Disciplines</span>: <span class="disciplines"><xsl:value-of select="disciplines"/></span></li>
           </ul>
           <div class="text">
             <xsl:call-template name="line-breaks">
               <xsl:with-param name="text" select="text" />
             </xsl:call-template>
           </div>
	     </xsl:for-each>
       </xsl:for-each>

      <xsl:for-each select="/deck/library/card[not(type=preceding-sibling::card/type)]">
        <xsl:sort select="type"/>
        <h4 class="librarytype"><xsl:value-of select="type"/></h4>
        <xsl:variable name="mytype" select="string(type)"/>
        <xsl:for-each select="//card[(type=$mytype) and not(name=preceding-sibling::card/name)]">
          <xsl:sort select="name"/>
          <h5 class="cardname"><xsl:value-of select="name"/></h5>
          <ul>
            <xsl:if test="requirement!=''">
              <li><span class="label">Requires</span>: <span class="requirement"><xsl:value-of select="requirement"/></span></li>
            </xsl:if>

            <xsl:if test="cost!=''">
                <li><span class="label">Cost</span>: <span class="cost"><xsl:value-of select="cost"/></span></li>
            </xsl:if>

            <xsl:if test="disciplines!=''">
              <li><span class="label">Disciplines</span>: <span class="disciplines"><xsl:value-of select="disciplines"/></span></li>
            </xsl:if>
          </ul>

          <div class="text">
            <xsl:call-template name="line-breaks">
              <xsl:with-param name="text" select="text" />
            </xsl:call-template>
          </div>
        </xsl:for-each>
      </xsl:for-each>
    </div>

    <div>
      <span class="generator">Crafted with :
        <xsl:value-of select="//deck/@generator"/><xsl:text>. [</xsl:text><xsl:value-of select="//deck/date"/><xsl:text>]</xsl:text>
      </span>
      <span class="taunt"> - Think you can make a better stylesheet ? Then do it boy !</span>
    </div>

  </body>
  </html>
</xsl:template>

<xsl:template name="LIBPART">
  <xsl:param name="mytype"/>
  <xsl:if test="//card[type = $mytype]">
  <div class="librarytable">
    <h4 class="librarytype"><span><xsl:value-of select="$mytype"/></span><span class="stats">[<xsl:value-of select="sum (//card[type = $mytype]/@count)"/>]</span></h4>
    <table><tbody>
      <xsl:for-each select="//card[(type=$mytype) and not(name=preceding-sibling::card/name)]">
        <xsl:sort select="name"/>
          <tr>
            <td><span class="tablevalue"><xsl:call-template name="count-cards"><xsl:with-param name="myname" select="string(name)" /></xsl:call-template>x</span></td>
            <td><span class="tablevalue"><a><xsl:attribute name='href'>http://monger.vekn.org/showcard.html?NAME=<xsl:value-of select="name"/></xsl:attribute><xsl:value-of select="name"/></a></span></td>
          </tr>
      </xsl:for-each>
    </tbody></table>
  </div>
  </xsl:if>
</xsl:template>

<xsl:template name="line-breaks">
  <xsl:param name="text"/>
  <xsl:choose>
    <xsl:when test="contains($text,'&#10;')">
      <xsl:value-of select="substring-before($text,'&#10;')"/>
      <br/>
      <xsl:call-template name="line-breaks">
        <xsl:with-param name="text" select="substring-after($text,'&#10;')"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$text"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="count-vampires">
<xsl:param name="myname"/>
<xsl:param name="myadv"/>
<xsl:value-of select="sum(//@count[../name=$myname and ../adv=$myadv])"/>
</xsl:template>

<xsl:template name="count-cards">
  <xsl:param name="myname"/>
  <xsl:value-of select="sum(//@count[../name=$myname])"/>
</xsl:template>

</xsl:stylesheet>
